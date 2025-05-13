import functools

def safe_llm_call(retries = 2, fallback = None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                
                except Exception as e:
                    print(f"[ERROR] Attempt {attempt + 1} failed in {func.__name__}: {e}")
                    
            print(f"[ERROR] All {retries + 1} attempts failed.")
            return fallback
        
        return wrapper
    
    return decorator

@safe_llm_call(retries = 2, fallback = None)
def invoke_llm_or_chains(llm_or_chains, input):
    return llm_or_chains.invoke(input)
