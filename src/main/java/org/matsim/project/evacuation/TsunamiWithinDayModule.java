package org.matsim.project.evacuation;

import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.core.controler.AbstractModule;
import org.matsim.core.router.util.TravelTime;
import org.matsim.withinday.trafficmonitoring.WithinDayTravelTime;

import jakarta.inject.Inject;
import jakarta.inject.Provider;
import java.util.HashSet;
import java.util.Set;

/**
 * Phase 3: Within-Day Replanning Module for Tsunami Evacuation.
 * 
 * This module enables agents to replan their routes when roads are closed
 * due to tsunami flooding.
 * 
 * Based on official MATSim example:
 * https://github.com/matsim-org/matsim-code-examples/tree/master/src/main/java/org/matsim/codeexamples/withinday
 */
public class TsunamiWithinDayModule extends AbstractModule {

    @Override
    public void install() {
        // Bind the within-day replanning listener
        this.addMobsimListenerBinding().to(TsunamiReplanningListener.class);

        // Bind WithinDayTravelTime for real-time travel time estimation
        bind(WithinDayTravelTimeProvider.class).asEagerSingleton();
        addEventHandlerBinding().to(WithinDayTravelTimeProvider.class);
        addMobsimListenerBinding().to(WithinDayTravelTimeProvider.class);
    }

    /**
     * Provider for WithinDayTravelTime that properly initializes with scenario.
     */
    public static class WithinDayTravelTimeProvider implements Provider<WithinDayTravelTime>,
            org.matsim.api.core.v01.events.handler.LinkEnterEventHandler,
            org.matsim.api.core.v01.events.handler.LinkLeaveEventHandler,
            org.matsim.core.mobsim.framework.listeners.MobsimBeforeSimStepListener {

        @Inject
        private Scenario scenario;
        private WithinDayTravelTime travelTime;

        @Override
        public WithinDayTravelTime get() {
            if (travelTime == null) {
                Set<String> analyzedModes = new HashSet<>();
                analyzedModes.add(TransportMode.car);
                travelTime = new WithinDayTravelTime(scenario, analyzedModes);
            }
            return travelTime;
        }

        @Override
        public void handleEvent(org.matsim.api.core.v01.events.LinkEnterEvent event) {
            if (travelTime != null) {
                travelTime.handleEvent(event);
            }
        }

        @Override
        public void handleEvent(org.matsim.api.core.v01.events.LinkLeaveEvent event) {
            if (travelTime != null) {
                travelTime.handleEvent(event);
            }
        }

        @Override
        public void notifyMobsimBeforeSimStep(org.matsim.core.mobsim.framework.events.MobsimBeforeSimStepEvent e) {
            if (travelTime != null) {
                travelTime.notifyMobsimBeforeSimStep(e);
            }
        }
    }
}
