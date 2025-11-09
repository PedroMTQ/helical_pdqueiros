import ray

ray.init("ray://localhost:10001")

@ray.remote
def f(x):
    return x * x

futures = [f.remote(i) for i in range(10)]
print(ray.get(futures))