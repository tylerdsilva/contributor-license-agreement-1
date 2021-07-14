# The line is of the format "+| `full name`| [gitLogin](https://github.com/gitLogin) |12-july-2021|"
from os import error


# Change line is of the format "+| `full name`| [pr_raiser_login](https://github.com/pr_raiser_login) |12-july-2021|"

def validate_change(pr_raiser_login, change):
    personal_cla_file = 'personal_contributor_licence_agreement.md'
    employer_cla_file = 'employer_contributor_license_agreement.md'
    # validation code here
    return False

# user names should be valid
EXPECTED_ERROR_MESSAGE = "Error: The expected line should be: | `full name` | [naren](https://github.com/naren) | 14-july-2021 | \n"
assert validate_change('naren', "+| `full name`| [some_wrong_user](https://github.com/naren) |14-july-2021|") == EXPECTED_ERROR_MESSAGE + 'Github username should be same as pull request user name'
assert validate_change('naren', "+| `full name`| [naren](https://github.com/some_wrong_user) |14-july-2021|") == EXPECTED_ERROR_MESSAGE + 'Github username should be same as pull request user name'
assert validate_change('naren', "+| 'full name'| [naren](https://github.com/some_wrong_user) |14-july-2021|") == EXPECTED_ERROR_MESSAGE + "please use `full name` instead of 'full name'"

# Date should be within one week of today and should be of the format dd-month-YYYY
DATE_ERROR_MESSAGE = EXPECTED_ERROR_MESSAGE + "Invalid date: date should be within one week of <today's date in dd-month-YYYY format>"
assert validate_change('naren', "+| `full name`| [naren](https://github.com/naren) |14-july-2020|") == DATE_ERROR_MESSAGE
assert validate_change('naren', "+| `full name`| [naren](https://github.com/naren) |14-06-2021|") == DATE_ERROR_MESSAGE
assert validate_change('naren', "+| `full name`| [naren](https://github.com/naren) ||") == DATE_ERROR_MESSAGE

# Invalid row fomatting
EXPECTED_ERROR_MESSAGE = "Error, invalid row format: The expected line should be: | `full name`| [naren](https://github.com/naren) |14-july-2021| \n"
assert validate_change('naren', "+ `full name`| [naren](https://github.com/naren) |14-july-2021|") == EXPECTED_ERROR_MESSAGE
assert validate_change('naren', "lols") == EXPECTED_ERROR_MESSAGE
assert validate_change('naren', "+| `full name` [naren](https://github.com/naren) |14-july-2021|") == EXPECTED_ERROR_MESSAGE
assert validate_change('naren', "+ `full name`| [nare") == EXPECTED_ERROR_MESSAGE
assert validate_change('naren', "+       | `full name`|   [naren](https://github.com/naren)  |14-july-2021  |   ") == EXPECTED_ERROR_MESSAGE + "Please remove extra spaces in the start of the line."

# check if already signed
EXPECTED_ERROR_MESSAGE = "Error,  Njay2000 has already signed the personal contributor license agreement."
assert validate_change('Njay2000', "+| `full name`| [Njay2000](https://github.com/Njay2000) |14-july-2021|") == EXPECTED_ERROR_MESSAGE
EXPECTED_ERROR_MESSAGE = "Error,  mathewdennis1 has already signed the employer contributor license agreement."
assert validate_change('mathewdennis1', "+| `full name`| [mathewdennis1](https://github.com/mathewdennis1) |14-july-2021|") == EXPECTED_ERROR_MESSAGE

# success case
EXPECTED_SUCCESS_MESSAGE = "ok"
assert validate_change('newuser', "+| `full name user` | [newuser](https://github.com/newuser) | 14-july-2021 |") == EXPECTED_SUCCESS_MESSAGE
assert validate_change('newuser', "+|`full name user`|[newuser](https://github.com/newuser)|14-july-2021|") == EXPECTED_SUCCESS_MESSAGE
assert validate_change('newuser', "+|  `full name user`   |    [newuser](https://github.com/newuser)   |  14-july-2021  |") == EXPECTED_SUCCESS_MESSAGE

print("success")
