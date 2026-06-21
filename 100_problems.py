#  squre star pattren


# len_of_squre=6
# width_of_squre=6
#
# for i in range(len_of_squre):
#     print(width_of_squre * " * ",)

# right angle star pattren

#
# len_of_triangle=6
# width_of_triangle=6
# num_of_star=5
#
# for i in range(len_of_triangle):
#     print((width_of_triangle - num_of_star)  * " * ",)
#     num_of_star-=1


# right  reverse angle star pattren


# len_of_rev_triangle=6
# width_of_rev_triangle=6
# num_of_star=1
#
# for i in range(len_of_rev_triangle):
#     print((width_of_rev_triangle - num_of_star)  * " * ",)
#     num_of_star+=1



# Pyramid star pattern
# row = 5
# for i in range(row):
#     spaces =row-i-1
#     star=2*i+1
#     print(" " * spaces+"*"*star)


#odd and even
# num=int(input("Enter the Number ==> "))
# if num % 2 == 0:
#     print(f"The Number \'{num}' is Even")
# else:
#     print(f"The Number \'{num}' is Odd")

#Find three Largest Number from list

# lst =[1,23,5,7,9,10]
# lst.sort(reverse=True)
# largest_num=lst[:3]
# print(largest_num)


#Multiplication Table
# mul_num=int(input("Enter the Number OF Table That You Want ."))
# mul_up_to=int(input("Enter the Number OF Table Up To Like (1-20) ."))
# for num in range(1,mul_up_to+1):
#     print(num,'*',mul_num,'=',num*mul_num)


# Find Factorial
# def factorial(num):
#     result=1
#     for i in range(1,num+1):
#         result*=i
#     return result
# print(factorial(5))
