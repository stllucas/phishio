"""Módulo de testes de carga utilizando Locust para simular acessos simultâneos à API."""
import random
from locust import HttpUser, task, between


URLS_CONHECIDAS = [f"https://example.com/cached_site_{i}" for i in range(50)]
"""Lista de 50 URLs fixas no escopo global para testar a funcionalidade de Cache HIT."""


class PhishioCheckUrlUser(HttpUser):
    """
    Classe que simula o comportamento de um usuário da extensão Phishio.
    Possui um tempo de espera configurado entre 5 e 10 segundos, simulando a leitura ou navegação entre abas.
    """
    wait_time = between(5, 10)

    def generate_random_dom(self):
        """Gera um conteúdo HTML (DOM) aleatório de tamanho razoável para popular o teste."""
        termos_phishing = ['banco', 'seguro', 'atualizacao', 'conta', 'cartao', 'token', 'urgente', 'pix', 'promocao', 'gratis']
        random_text = ' '.join(random.choices(termos_phishing, k=30))
        return f"<html><head><title>Test {random.randint(1, 100)}</title></head><body><h1>Hello</h1><p>{random_text}</p></body></html>"

    @task
    def test_check_url(self):
        """
        Simula requisição POST de verificação de URL no endpoint da API.
        Sorteia aleatoriamente uma das URLs base do sistema (garantindo que gerem Cache HITs após os primeiros envios) 
        e utiliza o interceptador de resposta para validar que o processamento não exceda a meta de 500ms.
        """
        url_test = random.choice(URLS_CONHECIDAS)
        payload = {
            "url": url_test,
            "dom": self.generate_random_dom()
        }

        with self.client.post("/check_url", json=payload, catch_response=True) as response:
            if response.elapsed.total_seconds() > 0.5:
                response.failure(
                    f"Falha na Meta: Tempo de resposta excedeu 500ms ({response.elapsed.total_seconds():.3f}s)")
            elif response.status_code != 200:
                response.failure(
                    f"Falha na requisição: Status {response.status_code}")
            else:
                response.success()
