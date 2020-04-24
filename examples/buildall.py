# Build the executables that are used in the flopy autotests

try:
    import pymake
except:
    print('pymake is not installed...will not build executables')
    pymake = None


def build_all():
    if pymake is not None:
        # build all of the applications
        pymake.build_apps()

        # build code json
        pymake.usgs_program_data.export_json(current=True)


if __name__ == '__main__':
    build_all()
