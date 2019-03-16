# Build the executables that are used in the flopy autotests

try:
    import pymake
except:
    print('pymake is not installed...will not build executables')
    pymake = None

def build_all():
    if pymake is not None:
        pymake.build_apps()

        # build code json
        pymake.usgs_prog_data.export_json(current=True)

if __name__ == '__main__':
    build_all()
