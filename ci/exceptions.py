"""
This module defines exceptions commonly used in scikit-ci.
"""

import os
import textwrap


class SKCIError(RuntimeError):
    """Exception raised when an scikit-ci error occurs.
    """
    pass


class SKCIStepExecutionError(SKCIError):
    """Exception raised when an error occurs while executing a step.
    """
    def __init__(self, step, return_code, cmd, output=None):
        self.step = step
        self.return_code = return_code
        self.cmd = cmd
        self.output = output

    def __str__(self):
        return textwrap.dedent(
            r"""
            A command failed while executing {step} step.
              Return code:
                {return_code}
              Command:
                {cmd}
              Working directory:
                {cwd}

            Please see above for more information.
            """.format(
                step=self.step.upper(),
                return_code=self.return_code,
                cmd=self.cmd,
                cwd=os.getcwd()
            )
        )
