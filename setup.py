from setuptools import setup, find_packages

with open("requirements.txt", "r") as f:
    install_requires = f.readlines()

setup(
    name="bizaxl_hrms",
    version="0.0.1",
    description="Bizaxl HRMS Portal - role-based HR self-service portal for Frappe v15 / ERPNext v15",
    author="Bizaxl HRMS Contributors",
    author_email="sudhakar+hrms@example.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)