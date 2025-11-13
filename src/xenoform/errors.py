class XenoformError(RuntimeError):
    pass


class AnnotationError(XenoformError):
    pass


class CompilationError(XenoformError):
    pass


class CppTypeError(XenoformError):
    pass
