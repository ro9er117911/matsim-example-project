package com.sun.media.imageioimpl.common;

/**
 * Shim to provide non-null metadata for the JAI ImageIO codecs shaded into pt2matsim.
 * The shaded jar loses manifest attributes, making the original PackageUtil return
 * null vendor/version and causing ImageIO service loading to fail. This replacement
 * returns fixed strings so the ImageWriter SPIs can be instantiated without error.
 */
public final class PackageUtil {
    private static final boolean CODEC_AVAILABLE = false;
    private static final String VERSION = "1.0";
    private static final String VENDOR = "Sun Microsystems, Inc.";
    private static final String SPEC_TITLE = "Java Advanced Imaging Image I/O Tools";

    private PackageUtil() {}

    public static boolean isCodecLibAvailable() {
        return CODEC_AVAILABLE;
    }

    public static String getVersion() {
        return VERSION;
    }

    public static String getVendor() {
        return VENDOR;
    }

    public static String getSpecificationTitle() {
        return SPEC_TITLE;
    }
}
