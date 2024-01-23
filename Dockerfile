# Stage 1: Set up the cross-compilation environment
FROM --platform=$BUILDPLATFORM tonistiigi/xx:latest AS xx

# Base image for the build
FROM --platform=$BUILDPLATFORM rust:bookworm AS build

# Copy the xx scripts for setting up the cross-compilation environment
COPY --from=xx / /

# Set up the working directory
WORKDIR /workspace

# Set RUSTFLAGS for static linking with the GNU toolchain
ENV RUSTFLAGS='-C target-feature=+crt-static'

# Install clang and other necessary tools
RUN apt-get update && \
    apt-get install -y clang lld

# Copy the Cargo.toml (and Cargo.lock if available) and source file into the image
COPY Cargo.toml Cargo.lock* ./

# Copy the Rust source file into the image
COPY src/main.rs ./src/

# Compile the program for the target platform
ARG TARGETPLATFORM
RUN xx-apt install -y gcc libc6-dev
RUN xx-cargo build --release --target-dir ./build
RUN xx-verify ./build/$(xx-cargo --print-target-triple)/release/arch-info

# Link the compiled binary into the workspace root
RUN ln -v ./build/$(xx-cargo --print-target-triple)/release/arch-info .

# Inspect the compiled binary
RUN file arch-info

# Stage 2: Create the final minimal output image
FROM scratch

# Copy the compiled binary from the build stage
COPY --from=build /workspace/arch-info /

# Set the entry point to the compiled binary
ENTRYPOINT ["/arch-info"]
