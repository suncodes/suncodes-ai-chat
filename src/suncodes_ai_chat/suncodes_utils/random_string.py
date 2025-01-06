import random
import string


def generate_random_string(length):
    # string.ascii_letters：所有字母（大小写）
    # string.digits：所有数字
    # string.punctuation：所有标点符号
    all_characters = string.ascii_lowercase + string.digits
    random_string = ''.join(random.choice(all_characters) for _ in range(length))
    return random_string
