// http://www.wisol.ch/w/articles/2015-07-26-virtual-keyboard-qt
// https://github.com/wisoltech/qt-virt-keyboard
// modified 2016 Dzoka

#include <QCoreApplication>
#include <QGuiApplication>
#include <QKeyEvent>
#include "keyemitter.h"

KeyEmitter::KeyEmitter()
{

}

KeyEmitter::~KeyEmitter()
{

}

void KeyEmitter::emitKey(Qt::Key key)
{
    QObject* receiver = QGuiApplication::focusObject();
    if(!receiver)
    {
        return;
    }
    QKeyEvent pressEvent = QKeyEvent(QEvent::KeyPress, key, Qt::NoModifier, QKeySequence(key).toString());
    QKeyEvent releaseEvent = QKeyEvent(QEvent::KeyRelease, key, Qt::NoModifier);
    QCoreApplication::sendEvent(receiver, &pressEvent);
    QCoreApplication::sendEvent(receiver, &releaseEvent);
}
