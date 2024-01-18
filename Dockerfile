# Stage 1: Set up the cross-compilation environment
FROM --platform=$BUILDPLATFORM tonistiigi/xx:latest AS xx

# Base image for the build
FROM --platform=$BUILDPLATFORM debian:bookworm AS build

# Copy the xx scripts for setting up the cross-compilation environment
COPY --from=xx / /

# Install build dependencies
RUN apt-get update && apt-get install -y \
    clang

# Set up the working directory
WORKDIR /workspace

# Copy the C source file into the image
COPY src/arch_info.c .

# Compile the program for the target platform
ARG TARGETPLATFORM
RUN xx-apt install -y libc6-dev gcc
RUN xx-clang --static -o arch_info arch_info.c

# Stage 2: Create the final minimal output image
FROM scratch

# Copy the compiled binary from the build stage
COPY --from=build /workspace/arch_info /

# Set the entry point to the compiled binary
ENTRYPOINT ["/arch_info"]
