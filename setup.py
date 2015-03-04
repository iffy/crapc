from setuptools import setup


def getVersion():
    import re, os
    r_version = re.compile(r'version\s=\s"(.*?)"')
    version_py = os.path.abspath(os.path.join(__file__,
                                 '../crapc/version.py'))
    return r_version.search(open(version_py, 'r').read()).groups()[0]


setup(
    url='none',
    author='Matt Haggard',
    author_email='haggardii@gmail.com',
    name='crapc',
    version=getVersion(),
    packages=[
        'crapc', 'crapc.test'
    ],
    install_requires=[
        'Twisted',
    ]
)