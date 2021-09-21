// modified from qt-virtual-numpad by Dzoka 2016

#include <QDesktopServices>
#include "setpos.h"
#include "ui_setpos.h"
#include "keyemitter.h"

#include <QDebug>

KeyEmitter keyEmitter;

// todo: coordinate with grbl and m_settings on unit conversion

setPos::setPos(QWidget *parent) :
    QDialog(parent),
    ui(new Ui::setPos)
{
    ui->setupUi(this);

	// compiles, not working as expected
	//ui->centralWidget->setWindowFlags( Qt::CustomizeWindowHint );
		
	QFont font = ui->pushButtonKey0->font();
	font.setPointSize(32);

	qDebug() << font;

	// why did font size change works in example, but not here ?
	// not only that, change style on all buttons leads to messed, non-uniformly compressed layout !
	
	foreach( QAbstractButton *button, ui->centralWidget->findChildren<QPushButton*>(QRegExp("pushButtonKey*"))){
		button->setFont(font);
	}

	// enter and back keys will be enlarged to accomodate text, so set a smaller one
	font.setPointSize(18);
	ui->pushButtonKeyEnter->setFont(font);
	ui->pushButtonKeyBack->setFont(font);
	ui->pushButtonKeySign->setFont(font);

	//ui->pushButtonKey0->setStyleSheet("border:1px solid lightgrey; border-radius: 10px" );
	//ui->pushButtonKey1->setStyleSheet("border:1px solid lightgrey; border-radius: 10px" );
	//ui->pushButtonKey2->setStyleSheet("border:1px solid lightgrey; border-radius: 10px" );
	//ui->pushButtonKey3->setStyleSheet("border:1px solid lightgrey; border-radius: 10px" );
	//ui->pushButtonKey4->setStyleSheet("border:1px solid lightgrey; border-radius: 10px" );
	//ui->pushButtonKey5->setStyleSheet("border:1px solid lightgrey; border-radius: 10px" );
	//ui->pushButtonKey6->setStyleSheet("border:1px solid lightgrey; border-radius: 10px" );
	//ui->pushButtonKey7->setStyleSheet("border:1px solid lightgrey; border-radius: 10px" );
	//ui->pushButtonKey8->setStyleSheet("border:1px solid lightgrey; border-radius: 10px" );
	//ui->pushButtonKey9->setStyleSheet("border:1px solid lightgrey; border-radius: 10px" );

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

	if( ui->pushButtonMode->text().contains( "Diameter" ) ){
		this->pos /= 2;
	}
	this->accept();  	// return from QDialog
}

void setPos::on_pushButtonCancel_clicked(){
	this->reject();
}

void setPos::updateAxisPos(){    // called before window pops up

	if( this->axis == "Z" ){
		ui->pushButtonMode->setText( "Set as Z=" );
		// may be set inactive ?
	}
	else{
		ui->pushButtonMode->setText( "Set as X (Radius)=" );
	}

	if( this->unit == 0 ){   // mm
		ui->pushButtonUnit->setText( "mm" );
	}
	else{
		ui->pushButtonUnit->setText( "inch" );
	}
	
	ui->lineEditPosition->setText( QString::number(this->pos) );
	ui->lineEditPosition->selectAll();
	ui->lineEditPosition->setFocus();
}

void setPos::on_pushButtonUnit_clicked(){

	
	QString unit = ui->pushButtonUnit->text();

	if( this->unit == 0 ){   // mm
		this->unit = 1;
		ui->pushButtonUnit->setText( "inch" );
	}
	else{
		this->unit = 0;
		ui->pushButtonUnit->setText( "mm" );
	}
	
	ui->lineEditPosition->setFocus();
}

void setPos::on_pushButtonMode_clicked(){
	QString mode = ui->pushButtonMode->text();

	if( this->axis == "Z" ){
		ui->lineEditPosition->setFocus();
		return;
	}
	
	if( mode.contains( "Diameter" ) ){
		ui->pushButtonMode->setText( "Set as X (Radius)=" );
	}
	else{
		ui->pushButtonMode->setText( "Set as Diameter=" );
	}

	ui->lineEditPosition->setFocus();
}
