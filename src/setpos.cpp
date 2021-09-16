// modified from qt-virtual-numpad by Dzoka 2016

#include <QDesktopServices>
#include "setpos.h"
#include "ui_setpos.h"
#include "keyemitter.h"

//#include <QDebug>

KeyEmitter keyEmitter;

setPos::setPos(QWidget *parent) :
    QDialog(parent),
    ui(new Ui::setPos)
{
    ui->setupUi(this);

	QFont font = ui->pushButtonKey0->font();
	font.setPointSize(32);

	foreach( QAbstractButton *button, ui->centralWidget->findChildren<QPushButton*>(QRegExp("pushButtonKey*"))){
		button->setFont(font);
	}

	// enter and back keys will be enlarged to accomodate text, so set a smaller one
	font.setPointSize(18);
	ui->pushButtonKeyEnter->setFont(font);
	ui->pushButtonKeyBack->setFont(font);
	ui->pushButtonKeySign->setFont(font);

}

setPos::~setPos(){
    delete ui;
}

void setPos::on_pushButtonKey0_clicked(){  keyEmitter.emitKey(Qt::Key_0); }
void setPos::on_pushButtonKey1_clicked(){  keyEmitter.emitKey(Qt::Key_1); }
void setPos::on_pushButtonKey2_clicked(){  keyEmitter.emitKey(Qt::Key_2); }
void setPos::on_pushButtonKey3_clicked(){  keyEmitter.emitKey(Qt::Key_3); }
void setPos::on_pushButtonKey4_clicked(){  keyEmitter.emitKey(Qt::Key_4); }
void setPos::on_pushButtonKey5_clicked(){  keyEmitter.emitKey(Qt::Key_5); }
void setPos::on_pushButtonKey6_clicked(){  keyEmitter.emitKey(Qt::Key_6); }
void setPos::on_pushButtonKey7_clicked(){  keyEmitter.emitKey(Qt::Key_7); }
void setPos::on_pushButtonKey8_clicked(){  keyEmitter.emitKey(Qt::Key_8); }
void setPos::on_pushButtonKey9_clicked(){  keyEmitter.emitKey(Qt::Key_9); }

void setPos::on_pushButtonKeyDot_clicked(){  keyEmitter.emitKey(Qt::Key_Period);    }
void setPos::on_pushButtonKeyBack_clicked(){ keyEmitter.emitKey(Qt::Key_Backspace); }

void setPos::on_pushButtonKeySign_clicked(){
	QString sr = ui->lineEditPosition->text();
	if( sr.at( 0 ) == '-' ){
		ui->lineEditPosition->setText( sr.remove(0,1) );
	}
	else{
		ui->lineEditPosition->setText( "-" + sr );
	}
}

void setPos::on_pushButtonKeyEnter_clicked(){
	this->pos = ui->lineEditPosition->text().toDouble();
	this->accept();  	// return from QDialog
}

void setPos::on_pushButtonCancel_clicked(){
	this->reject();
}

void setPos::updateAxisPos(){    // called before window pops up
	ui->lineEditPosition->setText( QString::number(this->pos) );
	ui->lineEditPosition->selectAll();
	ui->lineEditPosition->setFocus();
}


void setPos::on_pushButtonUnit_clicked(){

	QString unit = ui->pushButtonUnit->text();

	if( unit.at( 0 ) == 'm' ){
		ui->pushButtonUnit->setText( "inch" );
	}
	else{
		ui->pushButtonUnit->setText( "mm" );
	}
	
	ui->lineEditPosition->setFocus();
}

void setPos::on_pushButtonMode_clicked(){
	QString mode = ui->pushButtonMode->text();

	if( mode.at( 0 ) == 'D' ){
		ui->pushButtonMode->setText( "Radius, X" );
	}
	else{
		ui->pushButtonMode->setText( "Diameter" );
	}

	ui->lineEditPosition->setFocus();

}
