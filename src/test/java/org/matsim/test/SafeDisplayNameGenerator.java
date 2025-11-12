package org.matsim.test;

import java.lang.reflect.Method;

import org.junit.jupiter.api.DisplayNameGenerator;

/**
 * Safe DisplayNameGenerator for JUnit Jupiter — never throws, minimal stable names.
 */
public class SafeDisplayNameGenerator implements DisplayNameGenerator {
	@Override
	public String generateDisplayNameForClass(Class<?> testClass) {
		return testClass == null ? "UnknownTestClass" : testClass.getSimpleName();
	}

	@Override
	public String generateDisplayNameForNestedClass(Class<?> nestedClass) {
		return generateDisplayNameForClass(nestedClass);
	}

	@Override
	public String generateDisplayNameForMethod(Class<?> testClass, Method testMethod) {
		return testMethod == null ? "unknownMethod()" : testMethod.getName() + "()";
	}
}
