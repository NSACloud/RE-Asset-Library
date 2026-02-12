#include "MurmurHash3.h"
#include <cstdint>

extern "C" {

__declspec(dllexport)
uint32_t murmurhash3_32(const void* key, int len, uint32_t seed)
{
    uint32_t out;
    MurmurHash3_x86_32(key, len, seed, &out);
    return out;
}

__declspec(dllexport)
uint64_t pakHash(const void* keyA, int lenA, const void* keyB, int lenB, uint32_t seed, uint64_t* out)
{
    uint32_t hashLower;
    uint32_t hashUpper;
    MurmurHash3_x86_32(keyA, lenA, seed, &hashLower);
    MurmurHash3_x86_32(keyB, lenB, seed, &hashUpper);
    uint64_t pakHash = (static_cast<uint64_t>(hashLower) << 32) | static_cast<uint32_t>(hashUpper);
    return pakHash;
}

}