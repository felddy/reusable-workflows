/// Prints the architecture string based on the current compilation target.
///  - If the architecture is known, prints the architecture string and exits with code 0 (success).
///  - If the architecture is unknown, prints a message and exits with code 1 (error).
use std::process;

/// Entry point of the application.
fn main() {
    match get_architecture() {
        // If an architecture is identified, print it and exit with code 0 (success).
        Some(arch) => {
            println!("{}", arch);
            process::exit(0);
        }
        // If the architecture is unknown, print a message and exit with code 1 (error).
        None => {
            println!("Architecture: Unknown");
            process::exit(1);
        }
    }
}

/// Returns the architecture string based on the current compilation target.
///
/// Uses Rust's conditional compilation features to determine the architecture.
/// Returns `Some(arch_string)` if known, or `None` if the architecture is unknown.
fn get_architecture() -> Option<&'static str> {
    match std::env::consts::ARCH {
        // ARM 64-bit architecture
        "aarch64" => Some("linux/arm64"),
        // ARM architecture with further checks for specific versions
        "arm" => Some(if cfg!(target_feature = "v7") {
            "linux/arm/v7"
        } else if cfg!(target_feature = "v6") {
            "linux/arm/v6"
        } else {
            "linux/arm"
        }),
        // MIPS architecture with endian check
        "mips64" => Some(if cfg!(target_endian = "little") {
            "linux/mips64le"
        } else {
            "linux/mips64"
        }),
        // Other architectures without specific version checks
        "powerpc64" => Some("linux/ppc64le"),
        "riscv64" => Some("linux/riscv64"),
        "s390x" => Some("linux/s390x"),
        "x86_64" => Some("linux/amd64"),
        "x86" => Some("linux/386"),
        // Fallback case for unknown architectures
        _ => None,
    }
}
