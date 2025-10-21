package org.matsim.project.tools;

import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.population.Person;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.population.algorithms.XY2Links;
import org.matsim.core.population.io.PopulationWriter;
import org.matsim.core.router.PlanRouter;
import org.matsim.core.router.TripRouter;
import org.matsim.core.router.TripRouterFactoryBuilderWithDefaults;
import org.matsim.core.scenario.ScenarioUtils;
import org.matsim.core.utils.timing.TimeInterpretation;

import jakarta.inject.Provider;

public final class PreRoutePt {

	private PreRoutePt() {
	}

	public static void main(final String[] args) {
		final String configFile = args.length > 0 ? args[0] : "scenarios/equil/config.xml";
		final String outPlans = args.length > 1 ? args[1] : "scenarios/equil/population_routed.xml";

		final Config config = ConfigUtils.loadConfig(configFile);
		config.transit().setUseTransit(true);

		final Scenario scenario = ScenarioUtils.loadScenario(config);

		new XY2Links(scenario).run(scenario.getPopulation());

		final Provider<TripRouter> tripRouterProvider = TripRouterFactoryBuilderWithDefaults
				.createDefaultTripRouterFactoryImpl(scenario);
		final TripRouter tripRouter = tripRouterProvider.get();
		final PlanRouter planRouter = new PlanRouter(tripRouter, TimeInterpretation.create(config));

		for (Person person : scenario.getPopulation().getPersons().values()) {
			planRouter.run(person.getSelectedPlan());
		}

		new PopulationWriter(scenario.getPopulation()).write(outPlans);
		System.out.println("Wrote routed plans to: " + outPlans);
	}
}
