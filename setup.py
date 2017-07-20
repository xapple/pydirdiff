from distutils.core import setup

setup(
        name             = 'pydirdiff',
        version          = '1.1.0',
        description      = 'pydirdiff is a python package',
        long_description = open('README.md').read(),
        license          = 'MIT',
        url              = 'http://xapple.github.com/pydirdiff/',
        author           = 'Lucas Sinclair',
        author_email     = 'lucas.sinclair@me.com',
        packages         = ['pydirdiff'],
        scripts          = ['pydirdiff/pydirdiff'],
        install_requires = [],
    )
