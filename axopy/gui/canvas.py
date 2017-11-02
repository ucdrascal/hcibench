from PyQt5 import QtCore, QtGui, QtWidgets


class Canvas(QtWidgets.QGraphicsView):
    """A 2D canvas interface implemented using a QGraphicsView.

    This view essentially just holds a QGraphicsScene that grows to fit the
    size of the view, keeping the aspect ratio square. The scene is displayed
    with a gray border.
    """

    rect = (-100, -100, 200, 200) # x, y, w, h
    border_width = 1

    default_border_color = '#444444'
    default_bg_color = '#dddddd'

    def __init__(self, draw_border=True, bg_color=None, border_color=None,
                 parent=None):
        super().__init__(parent=parent)

        if bg_color is None:
            bg_color = self.default_bg_color
        self.bg_color = bg_color

        if border_color is None:
            border_color = self.default_border_color
        self.border_color = border_color

        self._init_scene()
        if draw_border:
            self._init_border()

    def _init_scene(self):
        scene = QtWidgets.QGraphicsScene()
        scene.setSceneRect(*self.rect)

        self.setScene(scene)
        self.setRenderHint(QtGui.QPainter.Antialiasing)

        self.setBackgroundBrush(QtGui.QColor(self.bg_color))

    def _init_border(self):
        rect = self.scene().sceneRect()
        pen = QtGui.QPen(QtGui.QColor(self.border_color), self.border_width)
        lines = [
            QtCore.QLineF(rect.topLeft(), rect.topRight()),
            QtCore.QLineF(rect.topLeft(), rect.bottomLeft()),
            QtCore.QLineF(rect.topRight(), rect.bottomRight()),
            QtCore.QLineF(rect.bottomLeft(), rect.bottomRight())
        ]
        for line in lines:
            self.scene().addLine(line, pen)

    def add_item(self, item):
        self.scene().addItem(item)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), QtCore.Qt.KeepAspectRatio)


class GraphicsItemWrapper(object):

    def move_to(self, x, y):
        self.setPos(x, y)

    def move_by(self, dx, dy):
        self.moveBy(dx, dy)


class Circle(QtWidgets.QGraphicsEllipseItem, GraphicsItemWrapper):

    def __init__(self, size, color='#333333'):
        self.size = size
        super().__init__(-size/2, -size/2, size, size)
        self.setBrush(QtGui.QColor(color))
        pen = QtGui.QPen(QtGui.QBrush(), 0)
        self.setPen(pen)

    def set_color(self, color):
        self.setBrush(QtGui.QColor(color))


class Cross(QtWidgets.QGraphicsItemGroup, GraphicsItemWrapper):

    default_size = 5

    def __init__(self, size=None, color='#333333'):
        super().__init__()
        if size is None:
            size = self.default_size
        self.size = size

        # horizontal line
        self.addToGroup(Line(-size/2, 0, size/2, 0))
        # vertical line
        self.addToGroup(Line(0, -size/2, 0, size/2))


class Line(QtWidgets.QGraphicsLineItem):

    def __init__(self, x1, y1, x2, y2, color='#333333'):
        super().__init__(x1, y1, x2, y2)
        self.width = 1

        pen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(color)),
                         self.width,
                         cap=QtCore.Qt.FlatCap)
        self.setPen(pen)