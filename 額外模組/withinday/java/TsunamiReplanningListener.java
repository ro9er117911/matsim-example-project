package org.matsim.project.evacuation;

import com.google.inject.Inject;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.network.Network;
import org.matsim.api.core.v01.population.Leg;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.core.mobsim.framework.HasPerson;
import org.matsim.core.mobsim.framework.MobsimAgent;
import org.matsim.core.mobsim.framework.MobsimDriverAgent;
import org.matsim.core.mobsim.framework.events.MobsimBeforeSimStepEvent;
import org.matsim.core.mobsim.framework.listeners.MobsimBeforeSimStepListener;
import org.matsim.core.mobsim.qsim.agents.WithinDayAgentUtils;
import org.matsim.core.mobsim.qsim.interfaces.MobsimVehicle;
import org.matsim.core.mobsim.qsim.interfaces.Netsim;
import org.matsim.core.mobsim.qsim.interfaces.NetsimLink;
import org.matsim.core.router.util.LeastCostPathCalculator;
import org.matsim.core.router.util.LeastCostPathCalculatorFactory;
import org.matsim.core.router.util.TravelDisutility;
import org.matsim.core.router.costcalculators.TravelDisutilityFactory;
import org.matsim.core.router.util.TravelTime;
import org.matsim.withinday.utils.EditRoutes;

import jakarta.inject.Singleton;
import java.util.*;

/**
 * Periodic Within-Day Replanning Listener for Tsunami Evacuation.
 * 
 * This listener:
 * 1. Triggers replanning every REPLAN_INTERVAL seconds after disaster time
 * 2. Only selects agents currently on affected (slow/closed) links
 * 3. Reroutes agents to avoid flooded roads
 * 
 * Compatible with staged NetworkChangeEvents that progressively close roads.
 */
@Singleton
public class TsunamiReplanningListener implements MobsimBeforeSimStepListener {

    private static final Logger log = LogManager.getLogger(TsunamiReplanningListener.class);

    // Configuration
    private static final double TSUNAMI_ALERT_TIME = 10800.0; // 03:00:00
    private static final double REPLAN_INTERVAL = 300.0; // Every 5 minutes
    private static final double SLOW_SPEED_THRESHOLD = 5.0; // m/s - links slower than this are "affected"

    @Inject
    private Scenario scenario;
    @Inject
    private LeastCostPathCalculatorFactory pathCalculatorFactory;
    @Inject
    private Map<String, TravelTime> travelTimes;
    @Inject
    private Map<String, TravelDisutilityFactory> travelDisutilityFactories;

    private EditRoutes editRoutes;
    private double lastReplanTime = -REPLAN_INTERVAL;
    private int totalReplanned = 0;

    @Override
    public void notifyMobsimBeforeSimStep(@SuppressWarnings("rawtypes") MobsimBeforeSimStepEvent event) {
        Netsim mobsim = (Netsim) event.getQueueSimulation();
        double now = mobsim.getSimTimer().getTimeOfDay();

        // Only start replanning after disaster alert time
        if (now < TSUNAMI_ALERT_TIME) {
            return;
        }

        // Check if enough time has passed since last replanning
        if (now - lastReplanTime < REPLAN_INTERVAL) {
            return;
        }

        lastReplanTime = now;

        // Find affected links (slow or closed)
        Set<Id<Link>> affectedLinks = getAffectedLinks(mobsim.getNetsimNetwork().getNetwork(), now);

        if (affectedLinks.isEmpty()) {
            return;
        }

        // Find agents on affected links
        List<MobsimAgent> agentsToReplan = getAgentsOnLinks(mobsim, affectedLinks);

        if (agentsToReplan.isEmpty()) {
            return;
        }

        log.info("========================================");
        log.info("PERIODIC REPLANNING @ " + formatTime(now));
        log.info("  Affected links: " + affectedLinks.size());
        log.info("  Agents to replan: " + agentsToReplan.size());
        log.info("========================================");

        int successCount = 0;
        int failCount = 0;

        for (MobsimAgent agent : agentsToReplan) {
            if (replanAgent(agent, mobsim, now)) {
                successCount++;
            } else {
                failCount++;
            }
        }

        totalReplanned += successCount;
        log.info("  Results: " + successCount + " success, " + failCount + " failed");
        log.info("  Total replanned so far: " + totalReplanned);
    }

    /**
     * Get links that are currently closed or severely degraded.
     * Only includes links with freespeed < 1.0 m/s (almost closed)
     */
    private Set<Id<Link>> getAffectedLinks(Network network, double now) {
        Set<Id<Link>> affected = new HashSet<>();

        for (Link link : network.getLinks().values()) {
            double freespeed = link.getFreespeed(now);

            // Only consider truly closed or nearly closed links
            if (freespeed < 1.0) { // Less than 3.6 km/h = practically closed
                affected.add(link.getId());
            }
        }

        return affected;
    }

    /**
     * Get agents currently driving on the specified links.
     */
    private List<MobsimAgent> getAgentsOnLinks(Netsim mobsim, Set<Id<Link>> targetLinks) {
        List<MobsimAgent> agents = new ArrayList<>();

        for (Id<Link> linkId : targetLinks) {
            NetsimLink link = mobsim.getNetsimNetwork().getNetsimLinks().get(linkId);
            if (link == null)
                continue;

            for (MobsimVehicle vehicle : link.getAllNonParkedVehicles()) {
                MobsimDriverAgent driver = vehicle.getDriver();
                if (driver != null) {
                    agents.add(driver);
                }
            }
        }

        return agents;
    }

    /**
     * Replan a single agent's current route.
     */
    private boolean replanAgent(MobsimAgent agent, Netsim mobsim, double now) {
        try {
            // Get modifiable plan
            Plan plan = WithinDayAgentUtils.getModifiablePlan(agent);
            if (plan == null) {
                return false;
            }

            // Check if agent is on a leg
            if (!(WithinDayAgentUtils.getCurrentPlanElement(agent) instanceof Leg)) {
                return false;
            }

            Leg leg = (Leg) WithinDayAgentUtils.getCurrentPlanElement(agent);

            // Only replan car trips (not PT)
            if (!leg.getMode().equals(TransportMode.car)) {
                return false;
            }

            // Initialize EditRoutes (lazy initialization)
            if (editRoutes == null) {
                TravelTime travelTime = travelTimes.get(TransportMode.car);
                if (travelTime == null) {
                    log.warn("No TravelTime for car mode");
                    return false;
                }

                TravelDisutilityFactory disutilityFactory = travelDisutilityFactories.get(TransportMode.car);
                if (disutilityFactory == null) {
                    log.warn("No TravelDisutilityFactory for car mode");
                    return false;
                }

                TravelDisutility travelDisutility = disutilityFactory.createTravelDisutility(travelTime);
                LeastCostPathCalculator pathCalculator = pathCalculatorFactory.createPathCalculator(
                        scenario.getNetwork(), travelDisutility, travelTime);

                editRoutes = new EditRoutes(scenario.getNetwork(), pathCalculator,
                        scenario.getPopulation().getFactory());
            }

            // Get current position in route
            Integer linkIdx = WithinDayAgentUtils.getCurrentRouteLinkIdIndex(agent);
            Person person = ((HasPerson) agent).getPerson();

            // Replan from current position
            editRoutes.replanCurrentLegRoute(leg, person, linkIdx, now);

            // Reset agent caches
            WithinDayAgentUtils.resetCaches(agent);

            return true;

        } catch (Exception e) {
            log.debug("Failed to replan agent " + agent.getId() + ": " + e.getMessage());
            return false;
        }
    }

    private String formatTime(double seconds) {
        int hours = (int) (seconds / 3600);
        int mins = (int) ((seconds % 3600) / 60);
        int secs = (int) (seconds % 60);
        return String.format("%02d:%02d:%02d", hours, mins, secs);
    }
}
