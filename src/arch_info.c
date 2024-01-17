#include <stdio.h>

int main()
{
#if defined(__x86_64__)
    printf("linux/amd64\n");
#elif defined(__aarch64__)
    printf("linux/arm64\n");
#elif defined(__riscv) && (__riscv_xlen == 64)
    printf("linux/riscv64\n");
#elif defined(__PPC64__) || defined(__ppc64__)
    printf("linux/ppc64le\n");
#elif defined(__s390x__)
    printf("linux/s390x\n");
#elif defined(__i386__)
    printf("linux/386\n");
#elif defined(__mips64) && defined(__MIPSEL__)
    printf("linux/mips64le\n");
#elif defined(__mips64)
    printf("linux/mips64\n");
#elif defined(__arm__) && defined(__ARM_ARCH_7A__)
    printf("linux/arm/v7\n");
#elif defined(__arm__) && (defined(__ARM_ARCH_6__) || defined(__ARM_ARCH_6J__) || defined(__ARM_ARCH_6K__) || defined(__ARM_ARCH_6Z__) || defined(__ARM_ARCH_6ZK__) || defined(__ARM_ARCH_6T2__))
    printf("linux/arm/v6\n");
#else
    printf("Architecture: Unknown\n");
#endif
    return 0;
}
