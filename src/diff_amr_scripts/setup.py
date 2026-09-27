from setuptools import find_packages, setup

package_name = 'diff_amr_scripts'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='saivenkat',
    maintainer_email='Saivenkatkadavergu@todo.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            "read_lidar = diff_amr_scripts.read_lidar:main",
            "obstacle_avoid = diff_amr_scripts.obstacle_avoid:main",
            "wall_follwer_node = diff_amr_scripts.wall_following:main",
            
        ],
    },
)
