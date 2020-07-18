import pymake


def make_mfusg():
    pymake.build_apps(["mfusg", "zonbudusg"])


if __name__ == "__main__":
    make_mfusg()
