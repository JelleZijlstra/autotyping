from libcst.codemod import CodemodTest
from autotyper.autotype import AutotypeCommand


class TestAutotype(CodemodTest):
    TRANSFORM = AutotypeCommand

    def test_noop(self) -> None:
        before = """
            def f():
                pass
        """
        after = """
            def f():
                pass
        """

        # By default, we do nothing.
        self.assertCodemod(before, after)

    def test_none_return(self) -> None:
        before = """
            def foo():
                pass

            def bar():
                return 1
        """
        after = """
            def foo() -> None:
                pass

            def bar():
                return 1
        """
        self.assertCodemod(before, after, none_return=True)

    def test_bool_param(self) -> None:
        before = """
            def foo(x = False, y = 0, z: int = False):
                pass
        """
        after = """
            def foo(x: bool = False, y = 0, z: int = False):
                pass
        """
        self.assertCodemod(before, after, bool_param=True)

    def test_annotate_optional(self) -> None:
        before = """
            def foo(uid=None, qid=None):
                pass

            def bar(uid):
                pass
        """
        after = """
            from my_types import Uid
            from typing import Optional

            def foo(uid: Optional[Uid]=None, qid=None):
                pass

            def bar(uid):
                pass
        """
        self.assertCodemod(before, after, annotate_optional=["uid:my_types.Uid"])
