#include <iostream>
#include <vector>
#include <random>

namespace xpr {

  void _call_and_print_result(intptr_t px) {
    typedef double (*fn_t)(double);
    fn_t f = reinterpret_cast<fn_t>(px);
    std::cout << f(32.0) << std::endl;
  }

  std::vector<double> 
  _metropolis_hastings(
  	intptr_t px, 
  	double prop_sigma, 
  	double x0, 
  	size_t iters,
  	size_t seed) 
  {
    typedef double (*fn_t)(double);
    fn_t f = reinterpret_cast<fn_t>(px);
    
    typedef std::default_random_engine PRNG;
    PRNG prng(seed);
    
    std::vector<double> op;
    
    std::normal_distribution<> proposal(0.0, prop_sigma);
    double xcur = x0;
    
    for(size_t i=0; i < iters; i++){
    	double xprop = xcur + proposal(prng);
    	double a = f(xprop) - f(xcur);
    	if(a > 0){
    		xcur = xprop;
    	} else{
    		std::bernoulli_distribution b(exp(a));
    		if (b(prng)) {
    			xcur = xprop;
    		} 
    	}
    	op.push_back(xcur);
    }
    
    return op;
  }

} // namespace xpr

