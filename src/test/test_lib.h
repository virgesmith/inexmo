#pragma once

#include <cstdint>

template <uint64_t N> uint64_t fibonacci_template() {
  if constexpr (N == 0) {
    return 0;
  } else if constexpr (N == 1) {
    return 1;
  } else {
    return fibonacci_template<N - 1>() + fibonacci_template<N - 2>();
  }
}

uint64_t fibonacci(uint64_t n);
uint64_t lucas(uint64_t n);
