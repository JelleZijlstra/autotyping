from libcst.codemod import CodemodTest
from autotyping.autotyping import AutotypeCommand


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

            def baz():
                return
        """
        after = """
            def foo() -> None:
                pass

            def bar():
                return 1

            def baz() -> None:
                return
        """
        self.assertCodemod(before, after, none_return=True)

    def test_scalar_return(self) -> None:
        before = """
            def foo():
                pass

            def bar():
                return 1

            def formatter(x):
                return "{}".format(x)

            def baz() -> float:
                return "not a float"

            def two_returns(condition):
                if condition:
                    return 42
                else:
                    return
        """
        after = """
            def foo():
                pass

            def bar() -> int:
                return 1

            def formatter(x) -> str:
                return "{}".format(x)

            def baz() -> float:
                return "not a float"

            def two_returns(condition):
                if condition:
                    return 42
                else:
                    return
        """
        self.assertCodemod(before, after, scalar_return=True)

    def test_asynq_return(self) -> None:
        before = """
            from asynq import asynq

            @asynq()
            def ret_none():
                yield bar.asynq()

            @asynq()
            def ret_int():
                yield bar.asynq()
                return 3

            @asink()
            def not_asynq():
                yield bar.asynq()
        """
        after = """
            from asynq import asynq

            @asynq()
            def ret_none() -> None:
                yield bar.asynq()

            @asynq()
            def ret_int() -> int:
                yield bar.asynq()
                return 3

            @asink()
            def not_asynq():
                yield bar.asynq()
        """
        self.assertCodemod(before, after, scalar_return=True, none_return=True)

    def test_bool_param(self) -> None:
        before = """
            def foo(x = False, y = 0, z: int = False):
                lambda x=False: None

            lambda x=False: None
        """
        after = """
            def foo(x: bool = False, y = 0, z: int = False):
                lambda x=False: None

            lambda x=False: None
        """
        self.assertCodemod(before, after, bool_param=True)

    def test_typed_params(self) -> None:
        before = """
            def foo(x=0, y=0.0, z=f"x", alpha="", beta="b" "a", gamma=b"a"):
                pass
        """
        after = """
            def foo(x: int=0, y: float=0.0, z: str=f"x", alpha: str="", beta: str="b" "a", gamma: bytes=b"a"):
                pass
        """
        self.assertCodemod(
            before,
            after,
            str_param=True,
            bytes_param=True,
            float_param=True,
            int_param=True,
        )

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

    def test_annotate_named_param(self) -> None:
        before = """
            def foo(uid, qid):
                pass

            def bar(uid=1):
                pass
        """
        after = """
            from my_types import Uid

            def foo(uid: Uid, qid):
                pass

            def bar(uid=1):
                pass
        """
        self.assertCodemod(before, after, annotate_named_param=["uid:my_types.Uid"])

    def test_annotate_magics(self) -> None:
        before = """
            def __str__():
                pass

            def __not_str__():
                pass
        """
        after = """
            def __str__() -> str:
                pass

            def __not_str__():
                pass
        """
        self.assertCodemod(before, after, annotate_magics=True)

    def test_exit(self) -> None:
        before = """
            def __exit__(self, typ, value, tb):
                pass

            def __aexit__(self, typ, value, tb):
                pass

            def __exit__(self, *args):
                pass

            def __exit__(self, a, b, c, d):
                pass
        """
        after = """
            from types import TracebackType
            from typing import Optional, Type

            def __exit__(self, typ: Optional[Type[BaseException]], value: Optional[BaseException], tb: Optional[TracebackType]):
                pass

            def __aexit__(self, typ: Optional[Type[BaseException]], value: Optional[BaseException], tb: Optional[TracebackType]):
                pass

            def __exit__(self, *args):
                pass

            def __exit__(self, a, b, c, d):
                pass
        """
        self.assertCodemod(before, after, annotate_magics=True)

    def test_annotate_imprecise_magics(self) -> None:
        before = """
            def __iter__():
                pass

            def __not_iter__():
                pass
        """
        after = """
            from typing import Iterator

            def __iter__() -> Iterator:
                pass

            def __not_iter__():
                pass
        """
        self.assertCodemod(before, after, annotate_imprecise_magics=True)
