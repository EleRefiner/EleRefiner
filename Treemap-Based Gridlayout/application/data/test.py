import numpy as np

# a = np.array([[1, 2, 3], [2, 3, 4]])
#
# b = np.array(a)
#
# b = b-b.min(axis=0)
# print(a, b)
#
# b = np.array([2, 3, 4])
# print(a*b)
#
#
cnt = 0
cnt2 = 0
n = 30
m = 900
for i in range(1, n+1):
    for j in range(1, i+1):
        for k in range(1, j+1):
            for l in range(1, k+1):
                cnt += np.power(l/n*900, 0.5)
                cnt2 += 2 * np.power(l/n*900, 0.5) * l
print(cnt, cnt2)

# def fun(a, b):
#     return (a*a+b*b)*a*b
#
# print(fun(6, 7)+ fun(6, 1)+ fun(6, 2))
# print(fun(6, 8)+ fun(1, 2)+ fun(5, 2))
# print(fun(6, 8)+ fun(6, 2))