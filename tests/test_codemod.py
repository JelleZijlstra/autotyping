from libcst.codemod import CodemodTest, CodemodContext
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

            @abstractmethod
            def very_abstract():
                pass

            @abc.abstractmethod
            def very_abstract_without_import_from():
                pass
        """
        after = """
            def foo() -> None:
                pass

            def bar():
                return 1

            def baz() -> None:
                return

            @abstractmethod
            def very_abstract():
                pass

            @abc.abstractmethod
            def very_abstract_without_import_from():
                pass
        """
        self.assertCodemod(before, after, none_return=True)

    def test_none_return_stub(self) -> None:
        before = """
            def foo():
                pass
        """
        after = """
            def foo():
                pass
        """
        self.assertCodemod(
            before,
            after,
            none_return=True,
            context_override=CodemodContext(filename="stub.pyi"),
        )

    def test_scalar_return(self) -> None:
        before = """
            def foo():
                pass

            def bar():
                return 1

            def return_not(x):
                return not x

            def formatter(x):
                return "{}".format(x)

            def old_school_formatter(x):
                return "%s" % x

            def bytes_formatter(x):
                return b"%s" % x

            def boolean_return(x, y, z):
                return x is y or x in z

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

            def return_not(x) -> bool:
                return not x

            def formatter(x) -> str:
                return "{}".format(x)

            def old_school_formatter(x) -> str:
                return "%s" % x

            def bytes_formatter(x) -> bytes:
                return b"%s" % x

            def boolean_return(x, y, z) -> bool:
                return x is y or x in z

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

    def test_annotate_optional_with_builtin(self) -> None:
        before = """
            def foo(number=None):
                pass

            def bar(number):
                pass
        """
        after = """
            from typing import Optional

            def foo(number: Optional[int]=None):
                pass

            def bar(number):
                pass
        """
        self.assertCodemod(before, after, annotate_optional=["number:int"])

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

    def test_annotate_magics_len(self) -> None:
        before = """
            def __len__():
                pass

            def __length_hint__():
                pass
        """
        after = """
            def __len__() -> int:
                pass

            def __length_hint__() -> int:
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

    def test_empty_elems(self) -> None:
        before = """
            def foo(iterables):
                zip(*(bar(it) for it in iterables))
        """
        after = """
            def foo(iterables) -> None:
                zip(*(bar(it) for it in iterables))
        """
        self.assertCodemod(before, after, none_return=True)

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

    def test_guessed_name(self) -> None:
        before = """
            def foo(name):
                pass
        """
        after = """
            def foo(name: str):
                pass
        """
        self.assertCodemod(before, after, guess_common_names=True)

    def test_guessed_name_optional(self) -> None:
        before = """
            def foo(name=None):
                pass
        """
        after = """
            from typing import Optional

            def foo(name: Optional[str]=None):
                pass
        """
        self.assertCodemod(before, after, guess_common_names=True)

    def test_guessed_and_named_param(self) -> None:
        before = """
            def foo(uid, qid):
                pass
            def bar(name):
                pass
        """
        after = """
            from my_types import Uid

            def foo(uid: Uid, qid):
                pass
            def bar(name: str):
                pass
        """
        self.assertCodemod(
            before,
            after,
            guess_common_names=True,
            annotate_named_param=["uid:my_types.Uid"],
        )

    def test_optional_guessed_and_annotate_optional(self) -> None:
        before = """
            def foo(real=None, qid=None):
                pass
            def bar(name=None):
                pass
        """
        after = """
            from my_types import Uid
            from typing import Optional

            def foo(real: Optional[Uid]=None, qid=None):
                pass
            def bar(name: Optional[str]=None):
                pass
        """
        self.assertCodemod(
            before,
            after,
            guess_common_names=True,
            annotate_optional=["real:my_types.Uid"],
        )

    def test_guess_type_from_argname1(self) -> None:
        before = """
            def foo(list_int, set_ints):
                ...
            def bar(iterator_bool, deque_float):
                ...
            def no_guess(list_widths, container_int):
                ...
        """
        after = """
            from typing import Deque, Iterator, List, Set

            def foo(list_int: List[int], set_ints: Set[int]):
                ...
            def bar(iterator_bool: Iterator[bool], deque_float: Deque[float]):
                ...
            def no_guess(list_widths, container_int):
                ...
        """
        self.assertCodemod(before, after, guess_common_names=True)

    def test_guess_type_from_argname2(self) -> None:
        before = """
            def foo(int_list, ints_list, intslist):
                ...
            def bar(width_list, words_list, bool_list):
                ...
            def no_guess(save_list, real_list, int_lists):
                ...
        """
        after = """
            from typing import List

            def foo(int_list: List[int], ints_list: List[int], intslist: List[int]):
                ...
            def bar(width_list: List[int], words_list: List[str], bool_list: List[bool]):
                ...
            def no_guess(save_list, real_list, int_lists):
                ...
        """
        self.maxDiff = None
        self.assertCodemod(before, after, guess_common_names=True)

    def test_guess_type_from_argname3(self) -> None:
        before = """
            def foo(list_of_int, tuple_of_ints):
                ...
            def bar(deque_of_alphas, list_of_string):
                ...
            def no_guess(list_of_save, list_of_reals, list_of_list_of_int):
                ...
        """
        after = """
            from typing import Deque, List, Tuple

            def foo(list_of_int: List[int], tuple_of_ints: Tuple[int]):
                ...
            def bar(deque_of_alphas: Deque[float], list_of_string: List[str]):
                ...
            def no_guess(list_of_save, list_of_reals, list_of_list_of_int):
                ...
        """
        self.assertCodemod(before, after, guess_common_names=True)

    def test_guess_type_from_argname4(self) -> None:
        before = """
            def foo(reals, texts):
                ...
            def bar(shuffles, saves):
                ...
            def no_guess(radiuss, radius_s):
                ...
        """
        after = """
            from typing import Sequence

            def foo(reals: Sequence[float], texts: Sequence[str]):
                ...
            def bar(shuffles: Sequence[bool], saves: Sequence[bool]):
                ...
            def no_guess(radiuss, radius_s):
                ...
        """
        self.assertCodemod(before, after, guess_common_names=True)

    def test_guess_type_from_argname_optional(self) -> None:
        before = """
            def foo(reals = None, set_of_int = None):
                ...
            def foo2(int_tuple = None, iterator_int = None):
                ...
            """
        after = """
            from typing import Iterator, Optional, Sequence, Set, Tuple

            def foo(reals: Optional[Sequence[float]] = None, set_of_int: Optional[Set[int]] = None):
                ...
            def foo2(int_tuple: Optional[Tuple[int]] = None, iterator_int: Optional[Iterator[int]] = None):
                ...
        """
        self.assertCodemod(before, after, guess_common_names=True)
