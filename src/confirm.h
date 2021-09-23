
#ifndef CONFIRM_H
#define CONFIRM_H

#include <QDialog>

namespace Ui {
class confirm;
}

class confirm : public QDialog
{
    Q_OBJECT

public:
    explicit confirm(QWidget *parent = 0);
    ~confirm();

	void setMessage( QString msg );
	void setTitle( QString ttl );

private slots:
	void on_pushButtonOK_clicked();
	void on_pushButtonCancel_clicked();

private:
    Ui::confirm *ui;
};

#endif // ONFIRM_H
