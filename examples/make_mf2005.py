import pymake


def make_mf2005():
    pymake.build_apps("mf2005", verbose=True)


if __name__ == "__main__":
    make_mf2005()
