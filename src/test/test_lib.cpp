/*
g++ -fPIC -c test_lib.cpp -o test_lib.o
# build static library:
ar rcs libstatic.a test_lib.o
# build dynamic library:
g++ -shared test_lib.o -o libshared.so
*/
#include "test_lib.h"

uint64_t fibonacci(uint64_t n) {
  return n < 2 ? n : fibonacci(n - 1) + fibonacci(n - 2);
}

// this symbol should be stripped when statically linked
uint64_t lucas(uint64_t n) {
  return n < 2 ? 2 - n : lucas(n - 1) + lucas(n - 2);
}
