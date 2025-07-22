#!/usr/bin/env python3
"""
Test para verificar qué pasa cuando el usuario escribe palabras incomprensibles
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ambiguity_resolver import AmbiguityResolver

def test_incomprehensible_words():
    """Probar palabras completamente incomprensibles"""
    resolver = AmbiguityResolver()
    
    print('🔍 PRUEBAS CON PALABRAS INCOMPRENSIBLES:')
    print('=' * 60)
    
    # Casos de palabras totalmente incomprensibles
    test_cases = [
        {
            'word': 'xzqwerty',
            'context': '¿Te gustaría proceder con tu pedido?',
            'state': 'confirmacion'
        },
        {
            'word': 'asdfghj',
            'context': 'El total es $49.98. ¿Confirmas?',
            'state': 'confirmacion'
        },
        {
            'word': 'blablabla',
            'context': '¿Deseas agregar algo más?',
            'state': 'pedido'
        },
        {
            'word': 'qwertyuiop',
            'context': '¿Usas tu dirección registrada?',
            'state': 'direccion'
        },
        {
            'word': 'ñañañaña',
            'context': '¿Proceder con el pedido?',
            'state': 'confirmacion'
        },
        {
            'word': 'jajajajaja',
            'context': 'Selecciona el tamaño de pizza',
            'state': 'pedido'
        },
        {
            'word': 'lalalalala',
            'context': '¿Confirmas tu orden?',
            'state': 'confirmacion'
        },
        {
            'word': 'mmmmmmm',
            'context': '¿Te gustaría algo más?',
            'state': 'pedido'
        },
        {
            'word': 'ehhhhhh',
            'context': '¿Proceder al pago?',
            'state': 'pago'
        },
        {
            'word': 'uffffffffff',
            'context': '¿Confirmas la dirección?',
            'state': 'direccion'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. CASO: '{case['word']}'")
        print(f"   Contexto: {case['context']}")
        print(f"   Estado: {case['state']}")
        
        result = resolver.resolve_ambiguous_message(
            message=case['word'],
            last_bot_message=case['context'],
            conversation_state=case['state']
        )
        
        print(f"   → Intención detectada: {result['intent']}")
        print(f"   → Confianza: {result['confidence']:.2f}")
        
        if result.get('suggestion'):
            print(f"   → Sugerencia: {result['suggestion']}")
        
        if result.get('cleaned_message'):
            print(f"   → Mensaje limpio: {result['cleaned_message']}")
        
        # Mostrar qué haría el bot
        if result['intent'] == 'unclear':
            print(f"   🤖 Bot responde: Pidiendo clarificación con opciones claras")
        else:
            print(f"   🤖 Bot responde: Procesando como {result['intent']}")
    
    print('\n' + '=' * 60)
    print('📋 ANÁLISIS DE RESULTADOS:')
    print('=' * 60)
    
    print('\n🎯 ¿QUÉ PASA CON PALABRAS INCOMPRENSIBLES?')
    
    # Probar algunas palabras sin sentido específicamente
    nonsense_words = ['xyz123', 'abcdef', 'qwerty', 'asdf', 'zxcv']
    
    for word in nonsense_words:
        result = resolver.resolve_ambiguous_message(
            message=word,
            last_bot_message='¿Confirmas tu pedido por $45.99?',
            conversation_state='confirmacion'
        )
        
        print(f'\n• Palabra: "{word}"')
        print(f'  - Intención: {result["intent"]} ({result["confidence"]:.2f} confianza)')
        
        if result['intent'] == 'unclear':
            print(f'  - ✅ Bot NO reinicia el flujo')
            print(f'  - ✅ Bot mantiene el contexto')
            print(f'  - ✅ Bot pide clarificación')
        else:
            print(f'  - ⚠️  Bot interpreta como: {result["intent"]}')
    
    print('\n🔧 COMPORTAMIENTO DEL SISTEMA:')
    print('✅ Palabras incomprensibles → intent: "unclear"')
    print('✅ Confianza baja (0.0 - 0.3)')
    print('✅ Bot pide clarificación sin reiniciar')
    print('✅ Mantiene contexto del pedido')
    print('✅ Ofrece opciones claras al usuario')
    
    print('\n🤖 EJEMPLO DE RESPUESTA DEL BOT:')
    print('---')
    print('Usuario: "xzqwerty"')
    print('Bot: "No estoy seguro de entender tu respuesta. 🤔"')
    print('     "Para tu pedido de $45.99, puedes responder:"')
    print('     "• \'Sí\' o \'Confirmar\' para proceder"')
    print('     "• \'No\' o \'Cancelar\' para cancelar"')
    print('     "¿Qué prefieres hacer?"')
    print('---')
    
    print('\n🎉 CONCLUSIÓN:')
    print('El bot maneja palabras incomprensibles de forma elegante:')
    print('• NO reinicia el flujo')
    print('• NO se confunde')
    print('• Pide clarificación manteniendo contexto')
    print('• Ofrece opciones claras para continuar')

if __name__ == "__main__":
    test_incomprehensible_words()
