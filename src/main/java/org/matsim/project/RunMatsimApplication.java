/* *********************************************************************** *
 * project: org.matsim.*												   *
 *                                                                         *
 * *********************************************************************** *
 *                                                                         *
 * copyright       : (C) 2008 by the members listed in the COPYING,        *
 *                   LICENSE and WARRANTY file.                            *
 * email           : info at matsim dot org                                *
 *                                                                         *
 * *********************************************************************** *
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *   See also COPYING, LICENSE and WARRANTY file                           *
 *                                                                         *
 * *********************************************************************** */
package org.matsim.project;

import org.apache.logging.log4j.core.tools.picocli.CommandLine;
import org.matsim.api.core.v01.Scenario;
import org.matsim.application.MATSimApplication;
import org.matsim.core.config.Config;
import org.matsim.core.controler.Controler;
import org.matsim.core.controler.OutputDirectoryHierarchy.OverwriteFileSetting;
import org.matsim.simwrapper.SimWrapperModule;

/**
 * @author nagel
 *
 */
@CommandLine.Command( header = ":: MyScenario ::", version = "1.0")
public class RunMatsimApplication extends MATSimApplication {

	public RunMatsimApplication() {
		super("scenarios/equil/config.xml");
	}

	public static void main(String[] args) {
		MATSimApplication.run(RunMatsimApplication.class, args);
	}

	@Override
	protected Config prepareConfig(Config config) {

		config.controller().setOverwriteFileSetting( OverwriteFileSetting.deleteDirectoryIfExists );

		// possibly modify config here

		// ---

		return config;
	}

	@Override
	protected void prepareScenario(Scenario scenario) {

		// possibly modify scenario here
		// Sanitize network attributes for Avro/SimWrapper compatibility
		for (org.matsim.api.core.v01.network.Link link : scenario.getNetwork().getLinks().values()) {
			for (String key : link.getAttributes().getAsMap().keySet().toArray(new String[0])) {
				if (key.contains(":")) {
					link.getAttributes().removeAttribute(key);
				}
			}
		}
		for (org.matsim.api.core.v01.network.Node node : scenario.getNetwork().getNodes().values()) {
			for (String key : node.getAttributes().getAsMap().keySet().toArray(new String[0])) {
				if (key.contains(":")) {
					node.getAttributes().removeAttribute(key);
				}
			}
		}

		// ---

	}

	@Override
	protected void prepareControler(Controler controler) {

		// possibly modify controler here

//		controler.addOverridingModule( new OTFVisLiveModule() ) ;
		controler.addOverridingModule( new SimWrapperModule() ) ;


		// ---
	}
}
