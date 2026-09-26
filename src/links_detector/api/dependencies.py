from fastapi import Request

from links_detector.finalizer import LinksFinalizer


def get_finalizer(request: Request) -> LinksFinalizer:
    return request.app.state.finalizer
