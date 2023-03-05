from multiprocessing import Process
from multiprocessing.dummy import Pool
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from time import time


def factorize(*numbers):
    result = []
    for num in numbers:
        res = []
        for i in range(1, num + 1):
            if num % i == 0:
                res.append(i)
        result.append(res)
    return result
# raise NotImplementedError()


if __name__ == '__main__':
    start = time()
    a, b, c, d = factorize(128, 255, 99999, 10651060)
    print(a, b, c, d, sep='\n')
    print(f'Done in {time() - start:.2f} seconds')

    assert a == [1, 2, 4, 8, 16, 32, 64, 128]
    assert b == [1, 3, 5, 15, 17, 51, 85, 255]
    assert c == [1, 3, 9, 41, 123, 271, 369, 813, 2439, 11111, 33333, 99999]
    assert d == [1, 2, 4, 5, 7, 10, 14, 20, 28, 35, 70, 140, 76079, 152158, 304316, 380395, 532553, 760790, 1065106,
                 1521580, 2130212, 2662765, 5325530, 10651060]

    start_two = time()
    pr = Process(target=factorize, args=(128, 255, 99999, 10651060))
    pr.start()
    print('Done 1 process in {:.3f} seconds'.format(time() - start_two))

    start_poll = time()
    with Pool(4) as p:
        result = p.map(factorize, [128, 255, 99999, 10651060])
        print('Done by 4 processes dummy in {:.3f} seconds'.format(time() - start_poll))

    start_pool_executor = time()
    with ProcessPoolExecutor(max_workers=4) as p:
        result_pr = p.map(factorize, [128, 255, 99999, 10651060])
        print('Done by 4 processes in {:.3f} seconds'.format(time() - start_pool_executor))

    start_thread_pool_executor = time()
    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(factorize, [128, 255, 99999, 10651060])
        print('Done by 4 threads in {:.3f} seconds'.format(time() - start_thread_pool_executor))
