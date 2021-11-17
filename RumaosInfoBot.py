##########################
#
#    RUMAOS_INFO_BOT
#
##########################

import os
import pathlib
ubic = str(pathlib.Path(__file__).parent)+"\\"

from DatosTelegram import id_Autorizados, bot_token, testbot_token
from DatosTelegram import testrumaos, rumaos_info
from runpy import run_path
import datetime as dt
import pytz
argTime = pytz.timezone('America/Argentina/Salta')

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram import ChatAction
from telegram.ext import Updater, CommandHandler
from telegram.ext import MessageHandler, Filters 
from telegram.ext import CallbackQueryHandler, CallbackContext
from telegram.ext import Defaults

from functools import wraps

from InfoLubri_y_RedMas.InfoPenetracionRedMas import penetracionRedMas
from InfoLubri_y_RedMas.InfoLubri import ventaLubri

#####//////////////######
# BOT Token selection for testing:
# 0 = RUMAOS_Info_bot
# 1 = RUMAOStest_bot
MODE = 0

if MODE == 1:
    token = testbot_token
    destinatarios = [testrumaos]
    print("\n//////////","USANDO TEST BOT","//////////\n")
else:
    token = bot_token
    destinatarios = [rumaos_info]
######//////////////######


# Function to find complete path to files
def find(name, path, type="file"):
    '''
    Find the path to folders or files.

    Args:
    name: name of file or folder
    path: starting path of search
     type: "file" or "dir" (default: "file")

    Return a string of the complete path to folder or file
    '''
    for root, dirs, files in os.walk(path):
        if type == "file":
            if name in files:
                return os.path.join(root, name)
        elif type == "dir":
            if name in dirs:
                return os.path.join(root, name)
        else:
            raise ValueError("'type' must be 'file' or 'dir'")


######//////////////######
# Where to find the report image files of:
# "Info_Morosos.png", "Info_VolumenVentas.png", etc
filePath_Info_Morosos = find("InfoMorosos", ubic, "dir") + "\\"
filePath_InfoVtaComb = find("InfoVtaCombustibles", ubic, "dir") + "\\"
filePath_InfoGrandesDeudas = find("InfoDeuda", ubic, "dir") + "\\"
filePath_Info_Despachos_Camioneros = \
    find("DespachosCamionerosRedmas", ubic, "dir") + "\\"
######//////////////######


#########################
# LOGGING MESSAGES
#########################

# logging.basicConfig(
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
#         , level=logging.INFO
# )
# logger = logging.getLogger(__name__)

import logging.handlers
FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATEFMT = "%Y-%m-%d %H:%M:%S"

if not os.path.exists(ubic + "log"):
    os.mkdir(ubic + "log")

# set up logging to file - see previous section for more details
logging.basicConfig(level=logging.INFO,
                    format=FORMAT,
                    datefmt=DATEFMT)
# define a Handler which writes INFO messages to a log file
filelog = logging.handlers.TimedRotatingFileHandler(
    ubic + "log\\bot_activity.log"
    , when="midnight"
    , backupCount=5
)
filelog.setLevel(logging.INFO)
# set a format
formatter = logging.Formatter(fmt=FORMAT, datefmt=DATEFMT)
# tell the handler to use this format
filelog.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger("").addHandler(filelog)
logger = logging.getLogger(__name__)



#########################
# FUNCTION DECORATORS
#########################

def restricted(func):
    """
        This will use a wrapper to create a decorator "@restricted", this 
        decorator can be placed prior to every function that needs to be 
        locked by user ID
    """
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in id_Autorizados:
            print("Unauthorized user, access denied for ID {}".format(user_id))
            update.message.reply_text("USUARIO NO AUTORIZADO")
            return
        return func(update, context, *args, **kwargs)
    return wrapped


def developerOnly(func):
    """
        This decorator will grant function access only to the developer
    """
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in [id_Autorizados[0]]:
            print("Unauthorized user, access denied for ID {}".format(user_id))
            update.message.reply_text("USUARIO NO AUTORIZADO")
            return
        return func(update, context, *args, **kwargs)
    return wrapped


def send_action(action):
    """
        Create decorator for handlers that sends "action" while processing
        func command.
            action: examples are ChatAction.TYPING or ChatAction.UPLOAD_PHOTO
    """
    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            context.bot.send_chat_action(update.effective_message.chat_id
                , action
            )
            return func(update, context,  *args, **kwargs)
        return command_func
    
    return decorator


#########################
# INLINE KEYBOARD BUTTONS
#########################

@restricted # NOTE: Access restricted to "start" function!
def start(update, context) -> None:
    # This will create inline buttons
    keyboard = [
        [
            InlineKeyboardButton("Info Deudas"
                , callback_data="Info Deudas")
            , InlineKeyboardButton("Volumen Ventas Ayer"
                , callback_data="Volumen Ventas Ayer")
        ]
        , [
            InlineKeyboardButton("Info Morosos"
                , callback_data="Info Morosos")
            , InlineKeyboardButton("Info Penetración"
                , callback_data="Info Penetración")
        ]
        , [
            InlineKeyboardButton("Info Despachos Camioneros"
                , callback_data="Info Despachos Camioneros")
            , InlineKeyboardButton("Info Ventas Lubri"
                , callback_data="Info Ventas Lubri")
        ]
        , [
            InlineKeyboardButton("Salir"
                , callback_data="Salir")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text("Por favor elija una opción:"
        , reply_markup=reply_markup
    )


#########################
# INLINE KEYBOARD BUTTONS ACTIONS
#########################

@send_action(ChatAction.UPLOAD_PHOTO)
def button(update, context) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered to avoid errors, even with empty
    query.answer()

    query.edit_message_text(text=f"Opción Seleccionada: {query.data}")

    # INFO MOROSOS
    if query.data == "Info Morosos":
        try:
            run_path(filePath_Info_Morosos+"Morosos.py")
            query.bot.send_photo(update.effective_chat.id
                , open(filePath_Info_Morosos+"Info_Morosos.png"
                    , "rb"
                )
            )
        except Exception as e:
            query.bot.send_message(update.effective_chat.id
                , text="Algo falló, revisar consola")
            logger.error("", exc_info=1)

    # INFO VOLUMEN VENTAS AYER
    elif query.data == "Volumen Ventas Ayer":
        try:
            run_path(filePath_InfoVtaComb+"TotalesPorCombustible.py")
            query.bot.send_photo(update.effective_chat.id
                , open(filePath_InfoVtaComb+"Info_VolumenVentas.png"
                    , "rb"
                )
            )
        except Exception as e:  
            query.bot.send_message(update.effective_chat.id
                , text="Algo falló, revisar consola")
            logger.error("", exc_info=1)

    # INFO GRANDES DEUDAS
    elif query.data == "Info Deudas":
        try:
            run_path(filePath_InfoGrandesDeudas+"GrandesDeudas.py")
            query.bot.send_photo(update.effective_chat.id
                , open(filePath_InfoGrandesDeudas+"Info_GrandesDeudores.png"
                    , "rb"
                )
            )
            query.bot.send_photo(update.effective_chat.id
                , open(filePath_InfoGrandesDeudas+"Info_GrandesDeudasPorVend.png"
                    , "rb"
                )
            )
        except Exception as e:  
            query.bot.send_message(update.effective_chat.id
                , text="Algo falló, revisar consola")
            logger.error("", exc_info=1)
    
    # INFO DESPACHOS CAMIONEROS
    elif query.data == "Info Despachos Camioneros":
        try:
            run_path(filePath_Info_Despachos_Camioneros+"DespachosCamion.py")
            query.bot.send_photo(update.effective_chat.id
                , open(filePath_Info_Despachos_Camioneros
                    + "Info_Despachos_Camioneros.png"
                    , "rb"
                )
            )
        except Exception as e:  
            query.bot.send_message(update.effective_chat.id
                , text="Algo falló, revisar consola")
            logger.error("", exc_info=1)

    # INFO PENETRACION
    elif query.data == "Info Penetración":
        try:
            penetracionRedMas()
            query.bot.send_photo(update.effective_chat.id
                , open(find("Info_PenetracionRedMas.png", ubic)
                    , "rb"
                )
            )
        except Exception as e:  
            query.bot.send_message(update.effective_chat.id
                , text="Algo falló, revisar consola")
            logger.error("", exc_info=1)
    
    # INFO VENTAS LUBRI
    elif query.data == "Info Ventas Lubri":
        try:
            ventaLubri()
            query.bot.send_photo(update.effective_chat.id
                , open(find("Info_VentaLubri.png", ubic)
                    , "rb"
                )
            )
        except Exception as e:  
            query.bot.send_message(update.effective_chat.id
                , text="Algo falló, revisar consola")
            logger.error("", exc_info=1)

    # EXIT OPTION
    elif query.data == "Salir":
        query.bot.send_message(update.effective_chat.id
            , text="Consulta Finalizada")

    else:
        query.bot.send_message(update.effective_chat.id
            , text="Algo no salió bien...")


#########################
# HELP COMMAND ANSWER
#########################

def help_command(update, context) -> None:
    update.message.reply_text(
        "->Comandos Públicos:\n"
        +"/help o /ayuda -> Muestra esta información.\n"
        +"->Comandos Restringidos:\n"
        +"/start o /informes -> Inicia consulta.\n"
        +"->Comandos Desarrollador:\n"
        +"/set (HH:MM) -> Define horario del informe diario.\n"
        +"/unset info_diario -> Detiene envío del informe diario.\n"
        +"/forzar_envio -> Activa el informe diario en 10seg"
    )


#########################
# UNKNOWN COMMAND ANSWER
#########################

# Show a message when the bot receive an unknown command
def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id
    , text="Disculpa, no entendí ese comando\n"
        +"¿Necesitas /ayuda?")


#########################
# "SET DAILY REPORT" COMMAND ANSWER
#########################

@developerOnly
def set_envioDiario(update, context) -> None:
    try:
        # Parse time of what is written in chat command
        horario = dt.datetime.strptime(context.args[0], "%H:%M")
        horario_tz = argTime.localize(horario).timetz() # Apply ARG timezone
        
        # Remove old job to update time
        job_removed = remove_job_if_exists("info_diario", context)

        # Setting daily task       
        context.job_queue.run_daily(envio_automatico
            , horario_tz
            , name="info_diario"
        )

        text = "Informe Diario seteado!"
        if job_removed:
            text = text + " Horario de envío actualizado."

        update.message.reply_text(text)

    except:
        update.message.reply_text("Escribir hora y minutos: /set (HH:MM)")


# def tareas(update,context) -> None:
#     """ Send a list of scheduled jobs to the console 
#  ----------> NEED IMPROVEMENT to be send to chat <----------
#     """
#     context.job_queue.print_PTB_jobs()


def remove_job_if_exists(name, context) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


#########################
# "REMOVE SCHEDULED REPORTS" COMMAND ANSWER
#########################

@developerOnly
def unset(update, context) -> None:
    """Remove the job if the user changed their mind."""
    try:
        task = context.args[0]
        job_removed = remove_job_if_exists(task, context)
        if job_removed:
            text = "Tarea " + task + " ha sido cancelada!"
        else:
            text= "No hay tarea programada con ese nombre."
        update.message.reply_text(text)
    except:
        update.message.reply_text(
            "Escribir nombre de la tarea: /unset (nombre_Tarea)")


#########################
# "FORCE DAILY REPORT" COMMAND ANSWER
#########################

@developerOnly
def forzar_envio(update, context) -> None:
    update.message.reply_text("Enviando informes al canal en 10 seg")
    context.job_queue.run_once(envio_automatico, 10, name="envio_forzado")


#########################
# DAILY REPORT
#########################

# Reset all reports and send them to the designated channel
def envio_automatico(context):
    print("\n->Comenzando generación de informes<-")

    try:
        run_path(filePath_Info_Morosos+"Morosos.py")
        print("Info Morosos reseteado")
    except Exception as e:
        context.bot.send_message(id_Autorizados[0]
            , text="Error al resetear Info Morosos"
        )
        logger.error("Error al resetear Info Morosos", exc_info=1)

    try:
        run_path(filePath_InfoVtaComb+"TotalesPorCombustible.py")
        print("Info TotalesPorCombustible reseteado")
    except Exception as e:
        context.bot.send_message(id_Autorizados[0]
            , text="Error al resetear Info TotalesPorCombustible"
        )
        logger.error("Error al resetear Info TotalesPorCombustible", exc_info=1)

    try:
        run_path(filePath_InfoGrandesDeudas+"GrandesDeudas.py")
        print("Info GrandesDeudas reseteado")
    except Exception as e:
        context.bot.send_message(id_Autorizados[0]
            , text="Error al resetear Info GrandesDeudas"
        )
        logger.error("Error al resetear Info GrandesDeudas", exc_info=1)

    try:
        run_path(filePath_Info_Despachos_Camioneros+"DespachosCamion.py")
        print("Info Despachos_Camioneros reseteado")
    except Exception as e:
        context.bot.send_message(id_Autorizados[0]
            , text="Error al resetear Info Despachos_Camioneros"
        )
        logger.error("Error al resetear Despachos_Camioneros", exc_info=1)

    try:
        penetracionRedMas()
        print("Info Penetracion_RedMas reseteado")
    except Exception as e:
        context.bot.send_message(id_Autorizados[0]
            , text="Error al resetear Info Penetracion_RedMas"
        )
        logger.error("Error al resetear Penetracion_RedMas", exc_info=1)
    
    try:
        ventaLubri()
        print("Info Venta_Lubricante reseteado")
    except Exception as e:
        context.bot.send_message(id_Autorizados[0]
            , text="Error al resetear Info Venta_Lubricante"
        )
        logger.error("Error al resetear Venta_Lubricante", exc_info=1)

    fechahoy = dt.datetime.now().strftime("%d/%m/%y")

    for ids in destinatarios:
        context.bot.send_message(ids, text="INFORMES AUTOMÁTICOS " + fechahoy)
        context.bot.send_photo(
            ids
            , open(filePath_InfoVtaComb+"Info_VolumenVentas.png", "rb")
            , "Venta Total por Combustible de Ayer"
        )
        context.bot.send_photo(
            ids
            , open(filePath_InfoGrandesDeudas+"Info_GrandesDeudores.png", "rb")
            , "Grandes Deudas"
        )
        context.bot.send_photo(
            ids
            , open(filePath_InfoGrandesDeudas+"Info_GrandesDeudasPorVend.png"
                , "rb")
            , "Grandes Deudas por Vendedor"
        )
        context.bot.send_photo(
            ids
            , open(filePath_Info_Morosos+"Info_Morosos.png", "rb")
            , "Morosos"
        )
        context.bot.send_photo(
            ids
            , open(filePath_Info_Despachos_Camioneros+
                "Info_Despachos_Camioneros.png", "rb")
            , "Despachos Camioneros"
        )
        context.bot.send_photo(
            ids
            , open(find("Info_PenetracionRedMas.png", ubic), "rb")
            , "Penetración RedMas"
        )
        context.bot.send_photo(
            ids
            , open(find("Info_VentaLubri.png", ubic), "rb")
            , "Venta Lubricantes"
        )
    print("")


#########################
# CONNECTION KEEP ALIVE
#########################

def keepAlive(context):
    '''
    Will send a message to an invalid Telegram ID to 
    keep alive the connection
    '''
    try:
        context.bot.send_message(0, text="Keep Alive")
    except:
        pass
    


#########################
# MAIN FUNCTION
#########################

def main() -> None:
    """Run the bot."""
    defaults = Defaults(tzinfo=argTime)

    # Create the Updater and pass your bot token.
    updater = Updater(token, defaults=defaults)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler(["start", "informes"], start
        , run_async=True))
    dispatcher.add_handler(CallbackQueryHandler(button
        , run_async=True))
    dispatcher.add_handler(CommandHandler(["help","ayuda"], help_command
        , run_async=True))
    dispatcher.add_handler(CommandHandler(["forzar_envio"], forzar_envio))
    dispatcher.add_handler(CommandHandler(["set"], set_envioDiario))
    dispatcher.add_handler(CommandHandler(["unset"], unset))
    # dispatcher.add_handler(CommandHandler(["tareas"], tareas))

    # Listening for wrong or unknown commands
    # MUST BE AT THE END OF THE HANDLERS!!!!!
    unknown_handler = MessageHandler(Filters.command, unknown
        , run_async=True)
    dispatcher.add_handler(unknown_handler)


    ############# TASKs ############

    # updater.job_queue.run_repeating(callback_minute, interval=60, first=10)
    # updater.job_queue.run_once(envio_automatico, 15)

    updater.job_queue.run_daily(envio_automatico
        , dt.time(11,0,0,tzinfo=argTime) 
        , name="info_diario"
    )

    # Keep Alive Task
    updater.job_queue.run_repeating(keepAlive, interval=210, first=10)

    ############# /TASKs ############

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()





if __name__ == "__main__":
    main()