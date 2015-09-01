#include <iostream>

namespace xpr {

  void _call_and_print_result(intptr_t px) {
    typedef double (*fn_t)(double);
    fn_t f = reinterpret_cast<fn_t>(px);
    std::cout << f(32.0) << std::endl;
  }


} // namespace xpr
