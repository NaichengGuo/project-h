from core.utils.collection import CollectionUtil


def test_sub():
    a = [1, 2, 3, 4, 5]
    b = [3, 4, 5, 6, 7]
    c = CollectionUtil.sub(a, b)
    print(c)
    assert c == [1, 2]
    print(a)
    print(b)


if __name__ == "__main__":
    test_sub()
