<template>
  <main class="about-us-page">
    <div class="about-card">
      <h2>Про наш проект: Спільнота Ідей</h2>

      <div class="project-description">
        <p>
          Ласкаво просимо до нашої платформи – простору, де ідеї знаходять своє життя та спільноту! Наш проект створений для того, щоб кожен міг поділитися своїми задумами, знайти однодумців та отримати допомогу в реалізації найсміливіших концепцій.
        </p>
        <p>
          <strong>У чому суть?</strong> Кожен користувач може опублікувати власну ідею, детально описавши її назву та суть. Якщо для втілення задуму потрібна допомога, автор може створити конкретні завдання, які стануть відкритими для спільноти.
        </p>
        <p>
          <strong>Взаємодія та підтримка:</strong> Інші учасники платформи можуть активно долучатися: залишати коментарі під ідеями, ділитися порадами, оцінювати потенціал або просто висловлювати свою підтримку. Це створює живе середовище для обговорення та вдосконалення кожної ініціативи.
        </p>
        <p>
          <strong>Від ідеї до реалізації:</strong> Наша платформа надає можливість не тільки обговорювати, але й діяти. Користувачі можуть братися за виконання створених завдань, безпосередньо контактувати з автором ідеї через зручний вбудований чат для узгодження деталей. Автори ідей також можуть додавати нові завдання в міру розвитку проекту.
        </p>
        <p>
          <strong>Гнучкість та контроль:</strong> Ми розуміємо, що обставини можуть змінюватися. Тому виконавці мають можливість відмовитися від завдання, якщо не можуть його виконати. З іншого боку, власник ідеї може відключити виконавця, якщо той не проявляє активності або не виходить на зв'язок, забезпечуючи таким чином прогрес у реалізації ідеї.
        </p>
        <p>
          Наша мета – створити динамічну та продуктивну екосистему, де народжуються, розвиваються та втілюються в життя інноваційні ідеї завдяки силі спільноти. Приєднуйтесь, діліться, співпрацюйте та творіть разом з нами!
        </p>
      </div>

      <div class="back-to-home">
        <a href="#" @click="goToMain">Повернутися на головну</a>
      </div>
    </div>
  </main>
</template>

<script>
import { useRouter } from "vue-router";

export default {
  setup() {
    const router = useRouter();

    const goToMain = () => {
      router.push({ name: 'MainPage' }); // Або router.push('/main-page');
    };

    return {
      goToMain,
    };
  },
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap');

.about-us-page {
  font-family: 'Poppins', sans-serif;
  background: linear-gradient(to bottom, #2b1055, #7597de); /* Запасний фон */
  background-image: url('../assets/img.jpg'); /* Переконайтеся, що шлях правильний */
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
  color: #f0f0f0;
}

.about-card {
  background: rgba(30, 25, 45, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 20px;
  padding: 2.5rem 3rem;
  box-shadow: 0 8px 35px rgba(0, 0, 0, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.12);
  width: 100%;
  max-width: 1600px;
  color: #f0f0f0;
  text-align: left;
}

.about-card h2 {
  font-size: 2.2rem;
  margin-bottom: 2rem;
  font-weight: 600;
  color: #ffffff;
  text-align: center;
  text-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

.project-description p {
  font-size: 1rem;
  line-height: 1.8;
  margin-bottom: 1.5rem;
  color: #e0e0e0;
}

.project-description p strong {
  color: #ffffff; /* Робимо акцент на підзаголовках в тексті */
  font-weight: 600;
}

.project-description p:last-child {
  margin-bottom: 0;
}

.back-to-home {
  margin-top: 2.5rem;
  text-align: center;
}

.back-to-home a {
  background-color: #007AFF;
  color: white;
  border: none;
  padding: 0.9rem 1.8rem;
  border-radius: 10px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
  text-decoration: none;
  display: inline-block;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
}

.back-to-home a:hover {
  background-color: #005bb5;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.4);
}

@media (max-width: 768px) {
  .about-card {
    padding: 2rem 1.5rem;
    max-width: 90%;
  }

  .about-card h2 {
    font-size: 1.8rem;
  }

  .project-description p {
    font-size: 0.95rem;
    line-height: 1.7;
  }

  .back-to-home a {
    padding: 0.8rem 1.5rem;
    font-size: 0.9rem;
  }
}
</style>