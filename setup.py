from setuptools import setup, find_packages

setup(
    name='mara-base',
    version='0.1',

    description="Mara base framework with the cli app and some base API modules.",

    install_requires=[ 'entrypoints'
    ],

    extras_require={
        'test': ['pytest',
                 'flask>=0.12', 'mara_page' # config views
        ],
    },

    dependency_links=[
    ],

    packages=find_packages(),

    author='Mara contributors',
    license='MIT',

    entry_points={
        'console_scripts': [
            'mara = mara_base.cli:main',
        ],
        'mara_base.mara_consumer': [
            'cli = mara_base.cli:register_declared_commands',
        ]
    },

)
