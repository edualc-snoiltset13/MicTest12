package com.abc_bank.abc_bank;

import com.abc_bank.abc_bank.auth_users.entity.User;
import com.abc_bank.abc_bank.enums.NotificationType;
import com.abc_bank.abc_bank.notification.dtos.NotificationDTO;
import com.abc_bank.abc_bank.notification.services.NotificationService;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync
@RequiredArgsConstructor
public class AbcBankApplication {

	private final NotificationService notificationService;
	public static void main(String[] args) {
		SpringApplication.run(AbcBankApplication.class, args);
	}
	@Bean
	CommandLineRunner runner(){
		return args -> {
            NotificationDTO notificationDTO = NotificationDTO.builder()
                    .recipient("tezziconic@gmail.com")
					.subject("hello testing email")
					.body("this is a test email body")
					.type(NotificationType.EMAIL)
                    .build();
			notificationService.sendEmail(notificationDTO,new User());
        };
	}
}
