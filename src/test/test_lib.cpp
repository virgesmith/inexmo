/* build static library:
g++ -fPIC -c test_lib.cpp -o test_lib.o; ar rcs libtest_lib.a test_lib.o
# shared library also works, but requires -Wl,-rpath=. when linking:
*/
#include "header.h"

uint64_t fibonacci(uint64_t n) {
  return n < 2 ? n : fibonacci(n - 1) + fibonacci(n - 2);
}
