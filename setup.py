from setuptools import setup
from pip.req import parse_requirements


def getVersion():
    import re, os
    r_version = re.compile(r'__version__\s=\s"(.*?)"')
    version_py = os.path.abspath(os.path.join(__file__,
                                 '../crapc/version.py'))
    return r_version.search(open(version_py, 'r').read()).groups()[0]


def parseRequirements():
    reqs = parse_requirements('requirements.txt')
    packages = []
    links = []
    for req in reqs:
        if req.url:
            links.append(str(req.url))
            packages.append(str(req.req))
        else:
            packages.append(str(req.req))
    return packages, links

install_requires, dependency_links = parseRequirements()



setup(
    url='none',
    author='Matt Haggard',
    author_email='haggardii@gmail.com',
    name='crapc',
    version=getVersion(),
    packages=[
        'crapc', 'crapc.test'
    ],
    install_requires=install_requires,
    dependency_links=dependency_links,
)