// 2016 Dzoka

#ifndef KEYEMITTER_H
#define KEYEMITTER_H

#include <QObject>

class KeyEmitter : public QObject
{
    Q_OBJECT

public:
    KeyEmitter();
    ~KeyEmitter();

public slots:
    void emitKey(Qt::Key key);
};

#endif // KEYEMITTER_H
