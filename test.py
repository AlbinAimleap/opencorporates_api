import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor

def make_request():
    url = "http://127.0.0.1:8000/search?query=1721%20REALESTATE%20HOLDINGS,%20LLC&use_cache=false"
    start_time = time.time()
    response = requests.get(url)
    end_time = time.time()
    return end_time - start_time, response.status_code

def stress_test(num_requests=100, concurrent_requests=10):
    response_times = []
    status_codes = []
    
    def worker():
        time_taken, status_code = make_request()
        response_times.append(time_taken)
        status_codes.append(status_code)

    with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
        futures = [executor.submit(worker) for _ in range(num_requests)]
        for future in futures:
            future.result()

    # Calculate statistics
    avg_response_time = statistics.mean(response_times)
    min_response_time = min(response_times)
    max_response_time = max(response_times)
    p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
    
    # Print results
    print(f"\nStress Test Results:")
    print(f"Total Requests: {num_requests}")
    print(f"Concurrent Requests: {concurrent_requests}")
    print(f"Average Response Time: {avg_response_time:.3f} seconds")
    print(f"Min Response Time: {min_response_time:.3f} seconds")
    print(f"Max Response Time: {max_response_time:.3f} seconds")
    print(f"95th Percentile Response Time: {p95_response_time:.3f} seconds")
    print(f"Success Rate: {status_codes.count(200)/len(status_codes)*100:.2f}%")

if __name__ == "__main__":
    stress_test()
