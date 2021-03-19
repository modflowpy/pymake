import pymake


def make_mfnwt():
    pymake.build_apps("mfnwt", verbose=True)


if __name__ == "__main__":
    make_mfnwt()
