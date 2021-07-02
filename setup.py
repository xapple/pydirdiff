from distutils.core import setup

setup(
        name             = 'pydirdiff',
        version          = '1.2.1',
        description      = 'pydirdiff is a python package for comparing directories.',
        long_description = open('README.md').read(),
        long_description_content_type = 'text/markdown',
        license          = 'MIT',
        url              = 'http://xapple.github.com/pydirdiff/',
        author           = 'Lucas Sinclair',
        author_email     = 'lucas.sinclair@me.com',
        packages         = ['pydirdiff'],
        scripts          = ['pydirdiff/pydirdiff'],
        install_requires = ['sh'],
    )
